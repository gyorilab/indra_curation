function addCurationRow(clickedRow) {
    // Create the row
    let curationRow = document.createElement('curation-row');
    curationRow.id = clickedRow.id + '-cur';

    // Add the row to the evidence row
    clickedRow.parentNode.insertBefore(curationRow, clickedRow.nextSibling);

    return curationRow.id;
}


function slideToggle(id) {
    const el = document.querySelector(`#${id}`);
    if(!el.dataset.open_height) {
        el.dataset.open_height = el.offsetHeight;
    }
    if (el.dataset.open === "true") {
        el.dataset.open = "false";
        el.style.height = '0px';
    }
    else {
        el.dataset.open = "true";
        el.style.height = el.dataset.open_height + 'px';
    }
}


// Turn on all the toggle buttons.
document.querySelectorAll('.curation_toggle')
   .forEach(function(toggle) {
       const clickedRow = document.querySelector(`#${toggle.dataset.parent_id}`);
       const cur_id = addCurationRow(clickedRow);
       toggle.onclick = () => {
           slideToggle(cur_id);
       };
       toggle.innerHTML = "&#9998;";
       toggle.style.display = 'inline-block';
   })


Vue.component('curation-row', {
    template: `
        <div v-if='display' class='row cchild' style='border-top: 1px solid #FFFFFF;'>
          <div class='col' style='padding: 0px; border-top: 1px solid #FFFFFF;'>
            <select v-model='error_type'>
                <option value='' selected disabled hidden>Select error type...</option>
                <option v-for='(option_label, option_value) in options'
                        v-bind:value='option_value'
                        :key='option_value'>
                    {{ option_label }}
                </option>
            </select>
            <div class='form' 
                 style='display:inline-block; 
                        vertical-align: middle; 
                        top: 0px'>
                <form name='user_feedback_form'>
                    <input type='text' 
                           v-model='comment'
                           maxlength='240'
                           name='user_feedback' 
                           placeholder='Optional description (240 chars)' 
                           value=''
                           style='width: 360px;'>
                </form>
            </div>
            <div class='curation_button'
                 style='display:inline-block; 
                        vertical-align: middle;'>
                <button
                    type='button'
                    class='btn btn-default btn-submit pull-right'
                    style='padding: 2px 6px'
                    :disabled='submitting'
                    v-on:click='submitForm'>Submit
                </button>
            </div>
            <div class='curation_button'
                 style='display:inline-block; 
                        vertical-align: middle;'>
                <button
                    type='button'
                    class='btn btn-default btn-submit pull-right'
                    style='padding: 2px 6px'
                    v-on:click='loadPriors'>Load Priors
                </button>
            </div>
            <div class='submission_status'
                 style='display:inline-block; 
                        vertical-align: middle;'>
              <a class='submission_status'></a>
            </div>
            <div v-if='data_entered'>
              error_type: {{ error_type }}<br>
              comment: {{ comment }}
            </div>
            <div v-if='message'>
              message: {{ message }}
            </div>
            <div v-if='priors'>
              <h5>Prior Curations</h5>
              <div v-for='entry in priors'>
                 <hr>
                 error_type: {{ entry.tag }}<br>
                 source_api: {{ entry.source }}<br>
                 date: {{ entry.date }}<br>
                 email: {{ entry.email }}<br>
                 comment: {{ entry.text }}<br>
              </div>
            </div>
          </div>
        </div>`,
    data: function() {
        return {
            is_on: true,
	    comment: '',
            error_type: '',
	    options: {
		correct: 'Correct',
		entity_boundaries: 'Entity Boundaries',
                grounding: 'Grounding',
                no_relation: 'No Relation',
                wrong_relation: 'Wrong Relation',
                act_vs_amt: 'Activity vs. Amount',
                polarity: 'Polarity',
                negative_result: 'Negative Result',
                hypothesis: 'Hypothesis',
                agent_conditions: 'Agent Conditions',
                mod_site: 'Modification Site',
                other: 'Other...'
            },
            submitting: false,
            message: "",
            priors: null,
        }
    },
    computed: {
        data_entered: function () {
            return Boolean(this.comment) || Boolean(this.error_type);
        },

        display: function () {
            if (this.icon)
                return this.icon.dataset.show == 'true';
            else
                return true;
        }
    },
    mounted: function () {
        this.stmt_row = this.$el.parentElement;
        this.pmid_row = this.stmt_row.children[parseInt(this.$attrs.id.split('-')[4])*2]
        this.icon = this.pmid_row.getElementsByClassName('curation_toggle')[0];
        this.source_hash = this.pmid_row.dataset.source_hash;
        this.stmt_hash = this.stmt_row.dataset.stmt_hash;
    },
    methods: {
        submitForm: function() {
            this.submitting = true;
            console.log('Submitting Curation:');
            console.log('Comment: ' + this.comment);
            console.log('Error Type: ' + this.error_type);
            if (!this.error_type) {
                alert('Please enter an error type or "correct" for the statement in the dropdown menu.');
                return;
            }

            if (!this.comment && this.error_type == 'other') {
                alert('Please describe the error when using option "other...".');
                return;
            }

            this.submitCuration();
            this.submitting = false;
        },

        loadPriors: function() {
            console.log("Loading prior curations.");
            this.getCurations();
        },

        clear: function () {
            this.error_type = "";
            this.comment = "";
        },

        submitCuration: async function() {
            let cur_dict = {
                error_type: this.error_type,
                comment: this.comment,
                source_hash: this.source_hash,
                stmt_hash: this.stmt_hash
            };
            console.log('Sending: ' + JSON.stringify(cur_dict));
            const resp = await fetch(CURATION_ADDR, {
                    method: 'POST',
                    body: JSON.stringify(cur_dict),
                    headers: {'Content-Type': 'application/json'}
                    });
            console.log('Response Status: ' + resp.status);
            switch (resp.status) {
                case 200:
                    this.submitting = false;
                    this.message = "Curation successful!";
                    this.clear();
                    this.icon.style = "color: #00FF00";
                    this.priors = this.prios
                    break;
                case 400:
                    this.message = resp.status + ": Bad Curation Data";
                    this.icon.style = "color: #FF0000";
                    break;
                case 500:
                    this.message = resp.status + ": Internal Server Error";
                    this.icon.style = "color: #FF0000";
                    break;
                case 504:
                    this.message = resp.status + ": Server Timeout";
                    this.icon.style = "color: 58D3F7";
                    break;
                default:
                    console.log("Unexpected error");
                    console.log(resp);
                    this.message = resp.status + ': Uncaught error';
                    this.icon.style = "color: #FF8000";
                    break;
            };

            const data = await resp.json();
            console.log('Got back: ' + JSON.stringify(data));
        },

        getCurations: async function() {
            const resp = await fetch(`${LIST_ADDR}/${this.stmt_hash}/${this.source_hash}`, {
                    method: 'GET',
                 });
            console.log('Response Status: ' + resp.status);
            const data = await resp.json();
            console.log('Got back: ' + JSON.stringify(data));
            this.priors = data;
            return;
        },
    }
})

var app = new Vue({el:'#curation-app'})

