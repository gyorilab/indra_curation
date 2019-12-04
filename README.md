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

There is no special installation required, besides having `indra`, `indra_db`,
and their various dependancies installed and available on your python path.


## Running

To run the tool, first make sure you have your INDRA Statements generated in a
pickle file somewhere, with path `/path/to/stmt/pickles`. You then start up
the service:

```
python /path/to/indra_curation/curation_service/app.py /path/to/stmt/pickles <curation-label> <your@email.com>
```

The first option indicates the _directory_ containing the statement pickles,
the second a label with which you want to tag these curations, so that you can
distinguish them from the rest for future analysis. The last option is your
email which distinguishes you as the curator.

This will begin a web service on your localhost, probably port 5000, the
output will specify in either case. For the rest of the discussion I will
assume port 5000.


## Curating

To begin curating the statements in, for example,
`/path/to/stmt/pickles/tp53_stmts.pkl`, navigate to
`http://localhost:5000/show/tp53_stmts` in your browser. The first time you do
this, it will generate an HTML file which is stored in the same directory
alongside the original pickle file, and sharing its name (with .html replacing
.pkl, of course). Future calls to `tp53_stmts` will simply reload the same
HTML file.

You can now begin exploring the statements and their evidence. To view prior
curations, click the button next to a curation called "Load Previous".

To submit a curation, simply fill out the form and click submit.

