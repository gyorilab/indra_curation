import sys
import pickle
import argparse

from flask import Flask, request, jsonify, url_for
from flask_cors import CORS

from jinja2 import Environment, ChoiceLoader

from indra.assemblers.html import HtmlAssembler
from indra.assemblers.html.assembler import loader as indra_loader


app = Flask(__name__)
CORS(app)


# Instantiate a jinja2 env.
env = Environment(loader=ChoiceLoader([app.jinja_loader, indra_loader]))

# Here we can add functions to the jinja2 env.
env.globals.update(url_for=url_for)


CURATIONS = []


@app.route('/curate', methods=['POST'])
def submit_curation():
    CURATIONS.append(dict(request.json))
    return jsonify({'status': 'good'}) 


@app.route('/curations', methods=['GET'])
def get_curations():
    return jsonify(CURATIONS)


def get_parser():
    parser = argparse.ArgumentParser(
        description=("Generate and enable curation using an HTML document "
                     "displaying the statements in the given pickle file.")
    )
    parser.add_argument('load_file',
                        help=("Either a pickle file containing a list of "
                              "INDRA Statements, from which an HTML file will "
                              "be generated, or else a previously-generated "
                              "HTML file."))
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.load_file.endswith('.pkl'):
        with open(args.load_file, 'rb') as f:
            stmts = pickle.load(f)
        html_assembler = HtmlAssembler(stmts, title='INDRA Curation',
                                       db_rest_url=request.url_root[:-1])
        template = env.get_template('curation_service/cur_stmts_view.html')
        content = html_assembler.make_model(template)
        html_filename = args.load_file.replace('.pkl', '.html')
        with open(html_filename, 'w') as f:
            f.write(content)
        print(f"Generated HTML from {len(stmts)} Statements.")
    elif args.load_file.endsiwth('.html'):
        print("Using existing html file.")
        html_filename = args.load_file
    else:
        print(f"Invalid input file: {args.input_file}")
        sys.exit(1)
    print(f"Please open {html_filename} in your browser.")

    app.run()


if __name__ == '__main__':
    main()
