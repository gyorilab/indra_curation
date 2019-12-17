Vue.component('curation-row', {
    template: `
        <div class='container' v-show='open'>
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
              <div class='curation_button'
                   style='display:inline-block; 
                          vertical-align: middle;'>
                  <button
                      type='button'
                      class='btn btn-default btn-submit pull-right'
                      style='padding: 2px 6px'
                      v-on:click='loadPrevious'>Load Previous
                  </button>
              </div>
              <div class='submission_status'
                   style='display:inline-block; 
                          vertical-align: middle;'>
                <a class='submission_status'></a>
              </div>
              <div v-show='message'>
                message: {{ message }}
              </div>
              <div v-if='previous'>
                <h5>Prior Curations</h5>
                <div v-for='entry in previous' class='row'>
                   <div class='col-3'>
                     {{ entry.date }}
                   </div>
                   <div v-for='attr in ["email", "error_type", "comment", "source"]'
                        class='col'>
                     <span v-if='entry[attr]'>
                       {{ entry[attr] }}
                     </span>
                     <span v-else>
                       <i>No {{ attr }} given.</i>
                     </span>
                   </div>
                </div>
              </div>
            </div>
          </div>
        </div>`,
    props: {
        open: Boolean,
        source_hash: String,
        stmt_hash: String
    },
    data: function() {
        return {
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
            previous: null,
        }
    },
    computed: {
        data_entered: function () {
            return Boolean(this.comment) || Boolean(this.error_type);
        },
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

        loadPrevious: function() {
            console.log("Loading previous curations.");
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
            const resp = await fetch(`${CURATION_LIST_ADDR}/${this.stmt_hash}/${this.source_hash}`, {
                    method: 'GET',
                 });
            console.log('Response Status: ' + resp.status);
            const data = await resp.json();
            console.log('Got back: ' + JSON.stringify(data));
            this.previous = data;
            return;
        },
    }
})

Vue.component('ref-link', {
    template: `
        <span v-if='href_url'>
          <a class='id_link'
             :title="title_text"
             v-on:mouseover="getLinkTitle"
             :href='href_url'
             target="_blank">
           {{ ref_id }}
          </a>
        </span>
        <span v-else>
          {{ ref_id }}
        </span>
        `,
    props: {
        ref_name: String,
        text_refs: Object,
    },
    computed: {
        href_url: function() {
            if (!this.ref_id)
                return "";

            var link;
            switch (this.ref_name.toUpperCase()) {
                case 'PMID':
                    link = "https://www.ncbi.nlm.nih.gov/pubmed/" + this.ref_id;
                    break;
                case 'PMCID':
                    link = "https://www.ncbi.nlm.nih.gov/pmc/articles/" + this.ref_id;
                    break;
                case 'DOI':
                    link = "https://dx.doi.org/" + this.ref_id;
                    break;
                default:
                    link = "";
                    break;
            }
            return link;
        },

        ref_id: function () {
            return this.text_refs[this.ref_name.toUpperCase()];
        },

        title_text: function () {
            if (this.article_title)
                return this.article_title;
            else
                return "Hover to see info.";
        }
    },
    data: function () {
        return {
            article_title: null 
        }
    },
    methods: {
        getLinkTitle: async function () {
            if (this.article_title)
                return;

            const entrez_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi';
            this.title_text = "Loading...";
            switch (this.ref_name.toUpperCase()) {
                case 'PMID':
                    id = this.ref_id;
                    db = 'pubmed';
                    break;
                case 'PMCID':
                    id = this.ref_id.slice(3,);
                    db = 'pmc';
                    break;
                default:
                    this.article_title = `Cannot retrieve titles for ${this.ref_name}'s.`;
                    return;
            }
            let url = `${entrez_url}?id=${id}&retmode=json&db=${db}`
            console.log(url);
            const resp = await fetch(url, {method: 'POST'});
            console.log(resp);
            const data = await resp.json();
            const pmd = data.result[id];
            let authorsStr = '';
            let n = 0; 
            for (let author of pmd.authors) {
                if (n > 2) {
                    authorsStr += ', ...';
                    break;
                }
                authorsStr += author.name;
                if (n < pmd.authors.length) {
                    authorsStr += ', ';
                }
                n += 1;
            }
            this.article_title = `${authorsStr}, "${pmd.title}", ${pmd.source}, ${pmd.pubdate}`;
        }
    }
})

Vue.component('evidence', {
    template: `
        <div class='container evidence'>
          <hr>
          <div class='row'>
            <div class='col-1'>
              <div class='row'>
                <div class='col-3 nvp curation_toggle text-center'
                     :class="{ 'has-curation-badge': num_curations }"
                     v-on:click='toggleCuration'
                     :title='num_curations'>
                  &#9998;
                </div>
                <div class='col-9 nvp src-api'>
                  {{ source_api }}
                </div>
              </div>
            </div>
            <div class='col-10' v-html='text'></div>
            <div class='col-1 text-right'>
              <ref-link ref_name='pmid' :text_refs='text_refs'/>
              <ref-link ref_name='pmcid' :text_refs='text_refs'/>
              <ref-link ref_name='doi' :text_refs='text_refs'/>
            </div>
          </div>
          <div class='row'>
            <div class='col'>
              <curation-row :open='curation_shown' :stmt_hash='stmt_hash'
                            :source_hash='source_hash'/>
            </div>
          </div>
        </div>
        `,
    props: {
        text: String,
        pmid: String,
        source_api: String,
        text_refs: Object,
        num_curations: Number,
        source_hash: String,
        stmt_hash: String
    },
    data: function() {
        return {
            curation_shown: false
        }
    },
    methods: {
        toggleCuration: function () {
            this.curation_shown = !this.curation_shown
        }
    }
})

Vue.component('stmt-display', {
    template: `
        <div class='stmts'>
          <div class='header-row'>
            <h3 v-bind:title="metadata_display">Statements</h3>
          </div>
          <div v-for='top_group in stmts' class='top-group-row' :key='top_group.html_key'>
            <h2 v-if='top_group.stmts_formatted.length > 1'
                v-html='top_group.label'></h2>
            <div v-for='mid_group in top_group.stmts_formatted'
                 class='stmt-group-row' :key='mid_group.short_name_key'>
              <h3 v-if='mid_group.stmt_info_list.length > 1'
                  v-html='mid_group.short_name'></h3>
              <div v-for='stmt in mid_group.stmt_info_list' class='stmt-row'
                   :key='mid_group.short_name_key + stmt.hash'>
                <h4>
                    <span v-html='stmt.english'></span>
                    <small class='badge badge-secondary badge-pill'>{{ stmt.evidence.length }}</small>
                </h4>
                <div v-for='ev in stmt.evidence'
                     :key='mid_group.short_name_key + stmt.hash + ev.source_hash'>
                  <evidence v-bind='ev' :stmt_hash='stmt.hash'/>
                </div>
              </div>
            </div>
          </div>
          </div>
        </div>

        `,
    props: {
        stmts: Array,
        metadata: Object,
        source_key_dict: Object,
    },
    data: function () {
        return {}
    },
    computed: {
        metadata_display: function () {
            let ret = '';
            if (this.metadata) {
                Object.entries(this.metadata).forEach((entry) => {
                    ret += entry[0] + ': ' + entry[1] + '\n';
                })
            }
            return ret;
        },
    },
    methods: {
    }
})

Vue.component('interface', {
    template: `
        <div class='interface'>
            <div class='form' 
                 style='display:inline-block; 
                        vertical-align: middle; 
                        top: 0px'>
                <form name='user_feedback_form'>
                  <select v-model='name'>
                      <option value='' selected disabled hidden>Select a collection of Statements...</option>
                      <option v-for='option  in options'
                              :value='option'
                              :key='option'>
                          {{ option }}
                      </option>
                  </select>
                </form>
            </div>
            <div class='stmt_button'
                 style='display:inline-block; 
                        vertical-align: middle;'>
                <button
                    type='button'
                    class='btn btn-default btn-submit pull-right'
                    style='padding: 2px 6px'
                    v-on:click='getStmts'>
                  Load
                </button>
            </div>
            <div v-if='stmts'>
                <h1>
                  Statement Results
                  <button
                      type='button'
                      class='btn btn-default btn-submit pull-right'
                      style='padding: 2px 6px'
                      title='Regnerate Results'
                      v-on:click='getStmts(true)'>
                    &#x1f5d8;
                  </button>
                </h1>
                <stmt-display :stmts='stmts'/>
            </div>
        </div>
        `,
    data: function () {
        return {
            stmts: null,
            name: '',
            options: null
        }
    },
    created: function () {
        this.getOptions()
    },
    methods: {
        getStmts: async function(regenerate=false) {
            const resp = await fetch(`${JSON_ADDR}${this.name}?regen=${regenerate}`, {method: 'GET'});
            console.log("getStmts response status: " + resp.status);
            const data = await resp.json();
            this.stmts = data;
            return;
        },

        getOptions: async function() {
            const resp = await fetch(`${LIST_ADDR}`, {method: 'GET'});
            console.log("getOptions response status: " + resp.status);
            const data = await resp.json();
            this.options = data;
            return;
        }
    }
})


var app = new Vue({el:'#curation-app'})

