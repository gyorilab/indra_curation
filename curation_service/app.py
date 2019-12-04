import pickle
import argparse
from os import path
from datetime import datetime

from flask import Flask, request, jsonify, url_for, abort, Response
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


@app.route('/show/<load_file>', methods=['GET'])
def load(load_file):
    # Get the full path to the file.
    load_file = path.join(WORKING_DIR, load_file)
    print(f"Attempting to load {load_file}")

    # Load or generate the HTML file (as needed)
    if path.exists(load_file + '.html'):
        load_file += '.html'
        print("Using existing html file.")
        html_filename = load_file
        with open(html_filename, 'r') as f:
            content = f.read()
    elif path.exists(load_file + '.pkl'):
        load_file += '.pkl'
        with open(load_file, 'rb') as f:
            stmts = pickle.load(f)
        html_assembler = HtmlAssembler(stmts, title='INDRA Curation',
                                       db_rest_url=request.url_root[:-1])
        template = env.get_template('curation_service/cur_stmts_view.html')
        content = html_assembler.make_model(template)
        html_filename = load_file.replace('.pkl', '.html')
        with open(html_filename, 'w') as f:
            f.write(content)
        print(f"Generated HTML from {len(stmts)} Statements.")
    else:
        print(f"Invalid input file: {load_file}")
        abort(400, (f"Invalid input file: neither {load_file}.pkl or "
                    f"{load_file}.html exist."))
        return

    print(f"Presenting {html_filename}")
    return content


@app.route('/curations/submit', methods=['POST'])
def submit_curation_to_db():
    # Unpack the request.
    hash_val = int(request.json.get('stmt_hash'))
    source_hash = int(request.json.get('source_hash'))
    text = request.json.get('comment')
    tag = request.json.get('error_type')
    print(f"Adding curation for stmt={hash_val} and source_hash={source_hash}")

    # Add a new entry to the database.
    source_api = CURATION_TAG
    ip = request.remote_addr
    try:
        dbid = submit_curation(hash_val, tag, CURATOR_EMAIL, ip, text,
                               source_hash, source_api)
    except BadHashError as e:
        abort(Response("Invalid hash: %s." % e.mk_hash, 400))
        return

    # Add the curation to the cache
    key = (hash_val, source_hash)
    entry = dict(request.json)
    entry.update(id=dbid, tag=tag, ip=ip, email=CURATOR_EMAIL,
                 source=source_api, date=datetime.now())
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
                              "to load."))
    parser.add_argument('tag',
                        help=('Give these curations a tag to separate them '
                              'out from the rest.'))
    parser.add_argument('email', help='Enter your, the curator\'s, email')
    return parser


def update_curations():
    CURATIONS['cache'] = {}

    attr_maps = ['tag', 'text', ('curator', 'email'), 'source', 'ip', 'date',
                 'id', ('pa_hash', 'stmt_hash'), 'source_hash']

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
    WORKING_DIR = path.abspath(args.working_dir)
    CURATION_TAG = args.tag
    CURATOR_EMAIL = args.email

    update_curations()

    app.run()
