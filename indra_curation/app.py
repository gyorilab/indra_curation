import argparse
import os
import json
import re
from typing import Optional

import pickle
import logging
from os import path, listdir
from datetime import datetime

from flask import Flask, request, jsonify, url_for, abort, Response, \
    render_template, Blueprint
from jinja2 import Environment, ChoiceLoader

from indra_curation.validation import validate_comment
from indra.assemblers.english import EnglishAssembler
from indra.assemblers.html import HtmlAssembler
from indra.assemblers.html.assembler import loader as indra_loader, \
    _format_stmt_text, _format_evidence_text
from indra.sources.indra_db_rest import get_curations, submit_curation, \
    IndraDBRestAPIError


logger = logging.getLogger("curation_service")


try:
    import boto3
except ImportError:
    boto3 = None
    logger.warning(
        "boto3 not installed. S3 functionality will not be available. Install boto3 to "
        "enable it."
    )

app = Flask(__name__)
# The point of this blueprint stuff is to make it possible
# to move these route functions into a different place from
# the WSGI and from the CLI that actually runs it
ui_blueprint = Blueprint("ui", __name__)


# Instantiate a jinja2 env.
env = Environment(loader=ChoiceLoader([app.jinja_loader, indra_loader]))

# Here we can add functions to the jinja2 env.
env.globals.update(url_for=url_for)


CURATIONS = {'last_updated': None, 'cache': {}}
WORKING_DIR = None
CURATION_TAG = None
CURATOR_EMAIL = None
PICKLE_SORTING = None
STARTUP_RELOAD = False
REVERSE_SORT = False
CHECK_SYNTAX = False


s3_path_patt = re.compile('^s3:([-a-zA-Z0-9_]+)/(.*?)$')


def _list_files(name):
    """List files with the given name."""
    m = s3_path_patt.match(WORKING_DIR)
    if m:
        if boto3 is None:
            raise ImportError("boto3 is required for s3 functionality.")

        # We're using s3
        s3 = boto3.client('s3')
        bucket, prefix = m.groups()

        # Extend the prefix with the filename
        prefix += name

        # Get the list of possible files
        list_resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if not list_resp['KeyCount']:
            logger.info(f"No files match prefix: {prefix}")
            return []
        ret = (f"s3:{bucket}/{e['Key']}" for e in list_resp['Contents'])
    else:
        ret = (path.join(WORKING_DIR, fn) for fn in listdir(WORKING_DIR)
               if fn.startswith(name))
    return ret


def _get_file(file_path):
    """Get a file of the given name."""
    m = s3_path_patt.match(file_path)
    if m:
        if boto3 is None:
            raise ImportError("boto3 is required for s3 functionality.")

        # We're using s3
        s3 = boto3.client('s3')
        bucket, key = m.groups()

        # Get the file from s3
        resp = s3.get_object(Bucket=bucket, Key=key)
        ret = resp['Body'].read()
    else:
        with open(file_path, 'rb') as f:
            ret = f.read()
    return ret


def _put_file(file_path, content):
    """Save a file with the given name."""
    m = s3_path_patt.match(file_path)
    if m:
        if boto3 is None:
            raise ImportError("boto3 is required for s3 functionality.")

        # We're using s3
        s3 = boto3.client('s3')
        bucket, key = m.groups()

        # Put the file on s3
        s3.put_object(Bucket=bucket, Key=key, Body=content)
    else:
        with open(file_path, 'w') as f:
            f.write(content)
    return


# Needs to match 'KEY1:VALUE1;KEY2:VALUE2;...'. Trailing ';' is optional.
# Let keys be case-insensitive alphabet strings and values be any alphanumeric strings.


@ui_blueprint.route('/list', methods=['GET'])
def list_names():
    assert WORKING_DIR is not None, "WORKING_DIR is not defined."

    # List all files under the prefix.
    options = set()
    for option in _list_files(''):
        if option.endswith('.pkl'):
            options.add(option.replace('.pkl', '')
                              .replace(WORKING_DIR, '')
                              .lstrip('/')
                        )
    return jsonify(list(options))


@ui_blueprint.route('/', methods=['GET'])
@ui_blueprint.route('/json', methods=['GET'])
def get_nice_interface():
    return render_template('curation_service/fresh_stmts_view.html')


@ui_blueprint.route('/json/<name>', methods=['GET'])
def get_json_content(name):
    global STARTUP_RELOAD, REVERSE_SORT
    assert WORKING_DIR is not None, "WORKING_DIR is not defined."

    logger.info(f"Attempting to load JSON for {name}")

    regenerate = request.args.get('regen', 'false') == 'true'

    if STARTUP_RELOAD:
        regenerate = True
        STARTUP_RELOAD = False

    if regenerate:
        logger.info(f"Will regenerate JSON for {name}")

    grouped = request.args.get('grouped', 'false') == 'true'

    # Select the correct file
    is_json = False
    file_path = None
    for option in _list_files(name):
        if option.endswith('.json') and not regenerate:
            file_path = option
            is_json = True
            break
        elif option.endswith('.pkl'):
            file_path = option

    if file_path is None:
        logger.error(f"Invalid name: {name}")
        abort(400, (f"Invalid name: neither {name}.pkl nor {name}.json "
                    f"exists in {WORKING_DIR}. If using s3 directory, "
                    f"remember to add the '/' to the end for your working "
                    f"directory."))
        return

    raw_content = _get_file(file_path)

    # If the file is JSON, just return it.
    if is_json:
        logger.info("Returning with cached JSON file.")
        return jsonify(json.loads(raw_content))

    # Get the pickle file.
    stmts = pickle.loads(raw_content)

    # Sort the statements
    if PICKLE_SORTING == "evidence":
        # Sort by evidence count
        # default is True, so reverse is False
        reverse = not REVERSE_SORT
        stmts = sorted(stmts, key=lambda s: len(s.evidence), reverse=reverse)
    elif PICKLE_SORTING == "stmt_hash":
        # Sort by statement hash
        stmts = sorted(stmts, key=lambda s: s.get_hash(), reverse=REVERSE_SORT)
    elif PICKLE_SORTING == "stmt_alphabetical":
        # Sort the statements alphabetically by statement type then agent name
        stmts = sorted(
            stmts, key=lambda s: (
                s.__class__.__name__, *(a.name for a in s.agent_list()),
            ),
            reverse=REVERSE_SORT
        )
    elif PICKLE_SORTING == "agents_alphabetical":
        # Sort the statements alphabetically by agent name, then statement type
        stmts = sorted(
            stmts,
            key=lambda s: (
                *(a.name for a in s.agent_list()), s.__class__.__name__
            ),
            reverse=REVERSE_SORT
        )
    # elif PICKLE_SORTING == "curation":
    #     pass # need to implement
    else:
        assert PICKLE_SORTING is None, \
            f"Invalid sorting: {PICKLE_SORTING}"

    # Build the JSON file.
    result = {'stmts': [], 'grouped': grouped}
    if grouped:
        # Do HTML assembly, then convert to JSON
        html_assembler = HtmlAssembler(stmts, title='INDRA Curation',
                                       db_rest_url=request.url_root[:-1],
                                       curation_dict=CURATIONS['cache'])
        ordered_dict = html_assembler.make_json_model()
        for key, group_dict in ordered_dict.items():
            group_dict['key'] = key
            result['stmts'].append(group_dict)
    else:
        for stmt in stmts:
            stmt_dict = {
                'evidence': _format_evidence_text(stmt, CURATIONS['cache']),
                'english': _format_stmt_text(stmt),
                'evidence_count': len(stmt.evidence),
                'hash': str(stmt.get_hash()),
                'source_count': None
            }
            result['stmts'].append(stmt_dict)

    # Save the file to s3
    json_file_path = file_path.replace('.pkl', '.json')
    logger.info(f"Saved JSON file to {json_file_path}")
    _put_file(json_file_path, json.dumps(result, indent=2))

    # Return the result.
    logger.info("Returning with newly generated JSON file.")
    return jsonify(result)


@ui_blueprint.route('/curations/submit', methods=['POST'])
def submit_curation_to_db():
    # Unpack the request.
    pa_hash = int(request.json.get('stmt_hash'))
    source_hash = int(request.json.get('source_hash'))
    text = request.json.get('comment')
    tag = request.json.get('error_type')
    logger.info(f"Adding curation for stmt={pa_hash} and source_hash={source_hash}")

    if CHECK_SYNTAX and text.strip():
        valid, msg = validate_comment(text)
        if not valid:
            abort(Response(msg, 422))

    # Add a new entry to the database.
    source_api = CURATION_TAG
    try:
        dbid = submit_curation(
            hash_val=pa_hash,
            tag=tag,
            curator_email=CURATOR_EMAIL,
            text=text,
            ev_hash=source_hash,
            source=source_api,
        )

    except IndraDBRestAPIError:
        abort(Response(f"Could not submit curation for hash: {pa_hash}.", 400))
        return

    # Add the curation to the cache
    key = (pa_hash, source_hash)
    entry = dict(request.json)
    entry.update(
        id=dbid, email=CURATOR_EMAIL, source=source_api, date=datetime.now()
    )
    if key not in CURATIONS['cache']:
        CURATIONS['cache'][key] = []
    CURATIONS['cache'][key].append(entry)

    # Respond
    res = {'result': 'success', 'ref': {'id': dbid}}
    logger.info("Got result: %s" % str(res))
    return jsonify(res)


@ui_blueprint.route('/curations/<stmt_hash>/<ev_hash>', methods=['GET'])
def get_curation(stmt_hash, ev_hash):
    time_since_update = datetime.now() - CURATIONS['last_updated']
    if time_since_update.total_seconds() > 3600:  # one hour
        update_curations()

    key = (int(stmt_hash), int(ev_hash))
    logger.info(f"Looking for curations matching {key}")
    relevant_curations = CURATIONS['cache'].get(key, [])
    logger.info("Returning with result:\n"
          + '\n'.join(str(e) for e in relevant_curations))

    return jsonify(relevant_curations)


@ui_blueprint.route('/curations', methods=['GET'])
def get_curation_list():
    time_since_update = datetime.now() - CURATIONS['last_updated']
    if time_since_update.total_seconds() > 3600:  # one hour
        update_curations()
    return jsonify([{'key': [str(n) for n in k], 'value': v}
                    for k, v in CURATIONS['cache'].items()])


@ui_blueprint.route('/curations/update_cache', methods=['POST'])
def update_curations_endpoint():
    update_curations()


# TODO add this inside main code in separate PR
app.register_blueprint(ui_blueprint)


def update_curations():
    # Todo: use CurationCache class from other repo?
    CURATIONS['cache'] = {}
    CURATIONS["curated_hashes"] = set()

    attr_maps = [('tag', 'error_type'), ('text', 'comment'),
                 ('curator', 'email'), 'source', 'date', 'id',
                 ('pa_hash', 'stmt_hash'), 'source_hash']

    # Build up the curation dict.
    curations = get_curations()
    for curation in curations:
        key = (curation["pa_hash"], curation["source_hash"])
        if key[0] is not None:
            CURATIONS["curated_hashes"].add(int(key[0]))
        if key not in CURATIONS['cache']:
            CURATIONS['cache'][key] = []

        cur_dict = {}
        for attr_map in attr_maps:
            if isinstance(attr_map, tuple):
                db_attr, dict_key = attr_map
                cur_dict[dict_key] = curation[db_attr]
            else:
                cur_dict[attr_map] = curation[attr_map]
        CURATIONS['cache'][key].append(cur_dict)

    CURATIONS['last_updated'] = datetime.now()
    logger.info(f"Loaded {len(CURATIONS['cache'])} curations into cache.")
    return


def main():
    parser = argparse.ArgumentParser(
        description="Generate and enable curation using an HTML document displaying statements."
    )
    parser.add_argument(
        "--tag",
        required=True,
        help="Assign a tag that identifies these curations (stored as 'source')."
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address of the curator."
    )
    parser.add_argument(
        "--directory",
        default=os.getcwd(),
        help="Directory containing files to load (local or S3)."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port on which the service runs."
    )
    parser.add_argument(
        "--statement-sorting",
        choices=["evidence", "stmt_hash", "stmt_alphabetical", "agents_alphabetical"],
        help="Method to sort statements."
    )
    parser.add_argument(
        "--reverse-sorting",
        action="store_true",
        help="Reverse the statement sorting order."
    )
    parser.add_argument(
        "--check-syntax",
        action="store_true",
        help="Check comment syntax for validity."
    )
    parser.add_argument(
        "--app-debug",
        action="store_true",
        help="Run the Flask app in debug mode."
    )

    args = parser.parse_args()
    global WORKING_DIR
    WORKING_DIR = args.directory
    logger.info(f"Working in {WORKING_DIR}")

    global CURATION_TAG
    CURATION_TAG = args.tag
    logger.info(f"Using tag {CURATION_TAG}")

    global CURATOR_EMAIL
    CURATOR_EMAIL = args.email
    logger.info(f"Curator email: {CURATOR_EMAIL}")

    global PICKLE_SORTING
    PICKLE_SORTING = args.statement_sorting

    global REVERSE_SORT
    REVERSE_SORT = args.reverse_sorting

    global CHECK_SYNTAX
    CHECK_SYNTAX = args.check_syntax

    global STARTUP_RELOAD
    STARTUP_RELOAD = False
    if PICKLE_SORTING is not None:
        logger.info(
            f"{'Reverse sorting' if REVERSE_SORT else 'Sorting'} "
            f"statements by {PICKLE_SORTING}"
        )
        STARTUP_RELOAD = True

    update_curations()

    app.run(port=args.port, debug=args.app_debug)


if __name__ == '__main__':
    main()
