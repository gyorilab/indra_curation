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
pickle file somewhere, with path `/path/to/workingdir`. You then start up
the service:

```
python /path/to/curation_service/app.py /path/to/workingdir <label> <your@email.com>
```

The first option indicates the _directory_ containing the statement pickles,
the second a label with which you want to tag these curations, so that you can
distinguish them from the rest for future analysis. The last option is your
email which distinguishes you as the curator.

This will begin a web service on your localhost, probably port 5000, the
output will specify in either case. For the rest of the discussion I will
assume port 5000.

You can also point to an s3 prefix instead of a location on your local disk.
You can indicate this by using prepending the "filepath" with `s3:`,
e.g. `s3:/prefix/for/workingdir/`. Note that because this is an s3 prefix, a trailing
slash is **NOT** assumed.


## Curating

You can now go to `localhost:5000/json` and select one of your pickle files
from the dropdown menu to begin curating. The back-end service will generate
and cache JSON, which can be forcefully reloaded by clicking the
<img src="https://bigmech.s3.amazonaws.com/indra-db/reload.png" width=10 height=10> button.

You can now begin exploring the statements and their evidence. To view prior
curations, click the button next to a curation called "Load Previous".

To submit a curation, simply fill out the form and click submit.

