import pickle
import argparse
from os import path

from flask import Flask, request, jsonify, url_for, abort, Response
from indra_db.exceptions import BadHashError

from jinja2 import Environment, ChoiceLoader

from indra.assemblers.html import HtmlAssembler
from indra.assemblers.html.assembler import loader as indra_loader


app = Flask(__name__)


# Instantiate a jinja2 env.
env = Environment(loader=ChoiceLoader([app.jinja_loader, indra_loader]))

# Here we can add functions to the jinja2 env.
env.globals.update(url_for=url_for)


CURATIONS = []
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


@app.route('/curate', methods=['POST'])
def submit_curation():
    hash_val = request.json.get('stmt_hash')
    print("Adding curation for statement %s." % hash_val)
    ev_hash = request.json.get('ev_hash')
    source_api = request.json.pop('source', 'INDRA CURATION')
    tag = CURATION_TAG
    ip = request.remote_addr
    text = request.json.get('text')
    try:
        dbid = submit_curation(hash_val, tag, CURATOR_EMAIL, ip, text, ev_hash,
                               source_api)
    except BadHashError as e:
        abort(Response("Invalid hash: %s." % e.mk_hash, 400))
        return
    CURATIONS.append(dict(request.json))
    CURATIONS[-1]['id'] = dbid
    res = {'result': 'success', 'ref': {'id': dbid}}
    print("Got result: %s" % str(res))
    return jsonify(res)


@app.route('/curations', methods=['GET'])
def get_curations():
    return jsonify(CURATIONS)


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


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    WORKING_DIR = path.abspath(args.working_dir)
    CURATION_TAG = args.tag
    CURATOR_EMAIL = args.email

    app.run()
