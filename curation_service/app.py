import json
import re
import boto3
import pickle
import argparse
from os import path, listdir
from datetime import datetime

from flask import Flask, request, jsonify, url_for, abort, Response, \
    render_template
from jinja2 import Environment, ChoiceLoader

from indra.assemblers.html import HtmlAssembler
from indra.assemblers.html.assembler import loader as indra_loader

from indra_db import get_db
from indra_db.client import submit_curation
from indra_db.exceptions import BadHashError


app = Flask(__name__)


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
            print(f"No files match prefix: {prefix}")
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


@app.route('/show/<name>', methods=['GET'])
def load(name):
    assert WORKING_DIR is not None, "WORKING_DIR is not defined."

    print(f"Attempting to load {name}")

    # Select the correct file
    is_html = False
    file_path = None
    for option in _list_files(name):
        if option.endswith('.html'):
            file_path = option
            is_html = True
            break
        elif option.endswith('.pkl'):
            file_path = option

    if file_path is None:
        print(f"ERROR: Invalid name: {name}")
        abort(400, (f"Invalid name: neither {name}.pkl nor {name}.html "
                    f"exists in {WORKING_DIR}. If using s3 directory, "
                    f"remember to add the '/' to the end for your working "
                    f"directory."))
        return

    raw_content = _get_file(file_path)

    # If the file is HTML, just return it.
    if is_html:
        print("Returning with cached HTML file.")
        return raw_content

    # Get the pickle file.
    stmts = pickle.loads(raw_content)

    # Build the HTML file
    html_assembler = HtmlAssembler(stmts, title='INDRA Curation',
                                   db_rest_url=request.url_root[:-1])
    template = env.get_template('curation_service/cur_stmts_view.html')
    content = html_assembler.make_model(template, with_grouping=False)

    # Save the file to s3
    html_file_path = file_path.replace('.pkl', '.html')
    print(f"Saved HTML file to {html_file_path}")
    _put_file(html_file_path, content)

    # Return the result.
    print("Returning with newly generated HTML file.")
    return content


@app.route('/json', methods=['GET'])
def get_nice_interface():
    return render_template('curation_service/fresh_stmts_view.html')


@app.route('/json/<name>', methods=['GET'])
def get_json_content(name):
    assert WORKING_DIR is not None, "WORKING_DIR is not defined."

    print(f"Attempting to load JSON for {name}")

    # Select the correct file
    is_json = False
    file_path = None
    for option in _list_files(name):
        if option.endswith('.json'):
            file_path = option
            is_json = True
            break
        elif option.endswith('.pkl'):
            file_path = option

    if file_path is None:
        print(f"ERROR: Invalid name: {name}")
        abort(400, (f"Invalid name: neither {name}.pkl nor {name}.json "
                    f"exists in {WORKING_DIR}. If using s3 directory, "
                    f"remember to add the '/' to the end for your working "
                    f"directory."))
        return

    raw_content = _get_file(file_path)

    # If the file is HTML, just return it.
    if is_json:
        print("Returning with cached JSON file.")
        return jsonify(json.loads(raw_content))

    # Get the pickle file.
    stmts = pickle.loads(raw_content)

    # Build the HTML file
    html_assembler = HtmlAssembler(stmts, title='INDRA Curation',
                                   db_rest_url=request.url_root[:-1])
    content = html_assembler.make_json_model()

    # Save the file to s3
    json_file_path = file_path.replace('.pkl', '.json')
    print(f"Saved JSON file to {json_file_path}")
    _put_file(json_file_path, json.dumps(content, indent=2))

    # Return the result.
    print("Returning with newly generated JSON file.")
    return jsonify(content)
    

@app.route('/curations/submit', methods=['POST'])
def submit_curation_to_db():
    # Unpack the request.
    pa_hash = int(request.json.get('stmt_hash'))
    source_hash = int(request.json.get('source_hash'))
    text = request.json.get('comment')
    tag = request.json.get('error_type')
    print(f"Adding curation for stmt={pa_hash} and source_hash={source_hash}")

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
    print("Got result: %s" % str(res))
    return jsonify(res)


@app.route('/curations/<stmt_hash>/<ev_hash>', methods=['GET'])
def get_curation(stmt_hash, ev_hash):
    time_since_update = datetime.now() - CURATIONS['last_updated']
    if time_since_update.total_seconds() > 3600:  # one hour
        update_curations()

    key = (int(stmt_hash), int(ev_hash))
    print(f"Looking for curations matching {key}")
    relevant_curations = CURATIONS['cache'].get(key, [])
    print("Returning with result:\n"
          + '\n'.join(str(e) for e in relevant_curations))

    return jsonify(relevant_curations)


@app.route('/curations', methods=['GET'])
def get_curation_list():
    time_since_update = datetime.now() - CURATIONS['last_updated']
    if time_since_update.total_seconds() > 3600:  # one hour
        update_curations()
    return jsonify([{'key': k, 'value': v}
                    for k, v in CURATIONS['cache'].items()])


@app.route('/curations/update_cache', methods=['POST'])
def update_curations_endpoint():
    update_curations()


def get_parser():
    parser = argparse.ArgumentParser(
        description=("Generate and enable curation using an HTML document "
                     "displaying the statements in the given pickle file.")
    )
    parser.add_argument('working_dir',
                        help=("The directory containing any files you wish "
                              "to load. This may either be local or on s3. If "
                              "using s3, give the prefix as "
                              "'s3:bucket/prefix/path/'. Without including "
                              "'s3:', it will be assumed the path is local. "
                              "Note that no '/' will be added automatically "
                              "to the end of the prefix."))
    parser.add_argument('tag',
                        help=('Give these curations a tag to separate them '
                              'out from the rest. This tag is stored as '
                              '"source" in the INDRA Database Curation '
                              'table.'))
    parser.add_argument('email', help='Enter your, the curator\'s, email')
    return parser


def update_curations():
    CURATIONS['cache'] = {}

    attr_maps = [('tag', 'error_type'), ('text', 'comment'),
                 ('curator', 'email'), 'source', 'ip', 'date', 'id',
                 ('pa_hash', 'stmt_hash'), 'source_hash']

    # Build up the curation dict.
    db = get_db('primary')
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
    return


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    WORKING_DIR = args.working_dir
    print(f"Working in {WORKING_DIR}")

    CURATION_TAG = args.tag
    print(f"Using tag {CURATION_TAG}")

    CURATOR_EMAIL = args.email
    print(f"Curator email: {CURATOR_EMAIL}")

    update_curations()

    app.run()
