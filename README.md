# INDRA Curation

This is a fairly simple wrapper surrounding the HTML assembler allowing a user
with direct access to the database to perform curations on custom generated
lists of INDRA Statements, stored in pickle files.

A key feature of this interface, which is a major improvement over the
current (as of this writing) INDRA Database interface is that you can load
and see previous curations for each piece of evidence. This is was made
practically possible by converting the curation interface to using Vue.js,
rather than the pure JavaScript used previously.


## Installation

There is no special installation required, besides having `indra`,
and its various dependencies installed and available on your python path.


## Running

To run the tool, first make sure you have your INDRA Statements generated in a
pickle file somewhere, with path `/path/to/workingdir`. You then start up
the service by running a variant of the following command:

```shell
python -m indra_curation.app --directory /path/to/workingdir --tag label --email your@email.com
```

This will begin a web service on your localhost.

Full usage (copied from `app.py --help`):

```
Usage: python -m indra_curation.app [OPTIONS]

  Generate and enable curation using an HTML document displaying the
  statements in the given pickle file.

Options:
  --tag TEXT                      Give these curations a tag to separate them
                                  out from the rest. This tag is stored as
                                  "source" in the INDRA Database Curation
                                  table.  [required]
  --email TEXT                    Email address of the curator  [required]
  --directory TEXT                The directory containing any files you wish
                                  to load. This may either be local or on s3.
                                  If using s3, give the prefix as
                                  's3:bucket/prefix/path/'. Without including
                                  's3:', it will be assumed the path is local.
                                  Note that no '/' will be added automatically
                                  to the end of the prefix.  [default:
                                  /home/klas/repos/indra_curation]
  --port INTEGER                  The port on which the service is running.
                                  [default: 5000]
  --statement-sorting [evidence|stmt_hash|stmt_alphabetical|agents_alphabetical]
                                  The sorting method to use for the pickled
                                  statements. If not provided, the statements
                                  will be sorted the way they are stored in
                                  the pickle file or the cache. Available
                                  options are:  - 'evidence' (sort by number
                                  of evidence, highest first),  - 'stmt_hash'
                                  (sort by statement hash),  -
                                  'stmt_alphabetical' (sort by statement type
                                  and alphabetically    by agent names),  -
                                  'agents_alphabetical' (sort by agent names,
                                  then by statement    type).
  --reverse-sorting               If provided, the statements will be sorted
                                  in reverse order. Does not apply if no
                                  sorting method is provided.
  --check-syntax                  If provided, the comment syntax will be
                                  checked for validity.
  --app-debug                     If provided, the Flask app will run in debug
                                  mode.
  --help                          Show this message and exit.
```

## Curating

You can now go to `localhost:5000/json` and select one of your pickle files
from the dropdown menu to begin curating. The back-end service will generate
and cache JSON, which can be forcefully reloaded by clicking the
<img src="https://bigmech.s3.amazonaws.com/indra-db/reload.png" width=10 height=10> button.

You can now begin exploring the statements and their evidence. To view prior
curations, click the button next to a curation called "Load Previous".

To submit a curation, simply fill out the form and click submit.

