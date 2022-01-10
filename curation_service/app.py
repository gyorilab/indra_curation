import os
import json
import re
import boto3
import click
import pickle
import logging
import argparse
from os import path, listdir
from datetime import datetime

from flask import Flask, request, jsonify, url_for, abort, Response, \
    render_template, Blueprint
from jinja2 import Environment, ChoiceLoader

from indra.assemblers.html import HtmlAssembler
from indra.assemblers.html.assembler import loader as indra_loader, \
    _format_stmt_text, _format_evidence_text

from indra_db import get_db
from indra_db.client import submit_curation
from indra_db.exceptions import BadHashError


logger = logging.getLogger("curation_service")

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


s3_path_patt = re.compile('^s3:([-a-zA-Z0-9_]+)/(.*?)$')


def _list_files(name):
    """List files with the given name."""
    m = s3_path_patt.match(WORKING_DIR)
    if m:
        # We're using s3
        s3 = boto3.client('s3')
        bucket, prefix = m.groups()

        # Extend the prefix with the filename
        prefix += name

        # Get the list of possible files, choose html if available, else pkl.
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
        # We're using s3
        s3 = boto3.client('s3')
        bucket, key = m.groups()

        # Put the file on s3
        s3.put_object(Bucket=bucket, Key=key, Body=content)
    else:
        with open(file_path, 'w') as f:
            f.write(content)
    return


@ui_blueprint.route('/list', methods=['GET'])
def list_names():
    assert WORKING_DIR is not None, "WORKING_DIR is not defined."

    # List all files under the prefix.
    options = set()
    for option in _list_files(''):
        for ending in ['.html', '.pkl']:
            if option.endswith(ending):
                options.add(option.replace(ending, '')
                                  .replace(WORKING_DIR, ''))
    return jsonify(list(options))


@ui_blueprint.route('/', methods=['GET'])
@ui_blueprint.route('/json', methods=['GET'])
def get_nice_interface():
    return render_template('curation_service/fresh_stmts_view.html')


@ui_blueprint.route('/json/<name>', methods=['GET'])
def get_json_content(name):
    assert WORKING_DIR is not None, "WORKING_DIR is not defined."

    logger.info(f"Attempting to load JSON for {name}")

    regenerate = request.args.get('regen', 'false') == 'true'
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

    # If the file is HTML, just return it.
    if is_json:
        logger.info("Returning with cached JSON file.")
        return jsonify(json.loads(raw_content))

    # Get the pickle file.
    stmts = pickle.loads(raw_content)

    # Build the HTML file
    result = {'stmts': [], 'grouped': grouped}
    if grouped:
        html_assembler = HtmlAssembler(stmts, title='INDRA Curation',
                                       db_rest_url=request.url_root[:-1],
                                       curation_dict=CURATIONS['cache'])
        ordered_dict = html_assembler.make_json_model()
        for key, group_dict in ordered_dict.items():
            group_dict['key'] = key
            result['stmts'].append(group_dict)
    else:
        for stmt in sorted(stmts,
                           key=lambda s: (len(s.evidence), s.get_hash()),
                           reverse=True):
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

    # Add a new entry to the database.
    source_api = CURATION_TAG
    ip = request.remote_addr
    try:
        dbid = submit_curation(pa_hash, tag, CURATOR_EMAIL, ip, text,
                               source_hash, source_api)
    except BadHashError as e:
        abort(Response("Invalid hash: %s." % e.mk_hash, 400))
        return

    # Add the curation to the cache
    key = (pa_hash, source_hash)
    entry = dict(request.json)
    entry.update(id=dbid, ip=ip, email=CURATOR_EMAIL, source=source_api,
                 date=datetime.now())
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
    CURATIONS['cache'] = {}

    attr_maps = [('tag', 'error_type'), ('text', 'comment'),
                 ('curator', 'email'), 'source', 'ip', 'date', 'id',
                 ('pa_hash', 'stmt_hash'), 'source_hash']

    # Build up the curation dict.
    db_key = "primary"
    db = get_db('primary')
    if db is None:
        raise RuntimeError(f"unable to get database: {db_key}")

    curations = db.select_all(db.Curation)
    for curation in curations:
        key = (curation.pa_hash, curation.source_hash)
        if key not in CURATIONS['cache']:
            CURATIONS['cache'][key] = []

        cur_dict = {}
        for attr_map in attr_maps:
            if isinstance(attr_map, tuple):
                db_attr, dict_key = attr_map
                cur_dict[dict_key] = getattr(curation, db_attr)
            else:
                cur_dict[attr_map] = getattr(curation, attr_map)
        CURATIONS['cache'][key].append(cur_dict)

    CURATIONS['last_updated'] = datetime.now()
    logger.info(f"Loaded {len(CURATIONS['cache'])} curations into cache.")
    return


@click.command(
    help="Generate and enable curation using an HTML document "
         "displaying the statements in the given pickle file."
)
@click.option(
    '--tag',
    required=True,
    help=('Give these curations a tag to separate them '
          'out from the rest. This tag is stored as '
          '"source" in the INDRA Database Curation '
          'table.')
)
@click.option('--email', required=True, help="Email address of the curator")
@click.option(
    '--directory',
    default=os.getcwd(),
    show_default=True,
    help=("The directory containing any files you wish "
          "to load. This may either be local or on s3. If "
          "using s3, give the prefix as "
          "'s3:bucket/prefix/path/'. Without including "
          "'s3:', it will be assumed the path is local. "
          "Note that no '/' will be added automatically "
          "to the end of the prefix."),
)
@click.option('--port', default="5000", help='The port on which the service is running.')
def main(tag: str, email: str, directory: str, port: str):
    global WORKING_DIR
    WORKING_DIR = directory
    logger.info(f"Working in {WORKING_DIR}")

    global CURATION_TAG
    CURATION_TAG = tag
    logger.info(f"Using tag {CURATION_TAG}")

    global CURATOR_EMAIL
    CURATOR_EMAIL = email
    logger.info(f"Curator email: {CURATOR_EMAIL}")

    update_curations()

    app.run(port=port)


if __name__ == '__main__':
    main()
