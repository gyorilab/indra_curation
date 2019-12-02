Vue.component('curation-row', {
    template: `
        <div class='row cchild' style='border-top: 1px solid #FFFFFF;'>
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
            message: ""
        }
    },
    computed: {
        data_entered: function () {
            return Boolean(this.comment) || Boolean(this.error_type);
        }
    },
    mounted: function () {
        this.pmid_row = this.$el.parentElement;
        this.icon = this.pmid_row.getElementsByClassName('curation_toggle')[0];
        this.source_hash = this.pmid_row.dataset.source_hash;
        this.stmt_hash = this.pmid_row.parentElement.dataset.stmt_hash;
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
            }
            console.log('Sending: ' + JSON.stringify(cur_dict));
            const resp = await fetch('http://127.0.0.1:5000/curate', {
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
            }

            const data = await resp.json();
            console.log('Got back: ' + JSON.stringify(data));
        }
    }
})

var app = new Vue({el:'#curation-app'})

