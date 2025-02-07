Vue.component('interface', {
    template: `
        <div class='interface'>
            <div class="input-group mb-3">
                <div class="input-group-prepend">
                    <button class="btn btn-outline-secondary btn-submit"
                            @click="getStmts(false)"
                            type="button">
                      Load Statement Set
                    </button>
                </div>
                <select class="custom-select"
                        id="stmt-set-select"
                        v-model="name"
                        aria-label="Select a collection of Statements">
                    <option v-for='option in options'
                            :value='option'
                            :key='option'>
                        {{ option }}
                    </option>
                </select>
            </div>
            <div v-if='stmts'>
                <h1>
                  Statement Results
                  <button
                      type='button'
                      class='btn btn-default btn-submit pull-right'
                      style='padding: 2px 6px'
                      title='Regenerate Results'
                      @click='getStmts(true)'>
                    <img src='https://bigmech.s3.amazonaws.com/indra-db/reload.png' style='width: 1em; height: 1em'>
                  </button>
                </h1>
                <stmt-display :stmts='stmts' :grouped='grouped' :autoload='true'/>
            </div>
        </div>
        `,
    data: function () {
        return {
            stmts: null,
            name: '',
            options: null,
            grouped: true
        }
    },
    created: function () {
        this.getOptions()
    },
    methods: {
        getStmts: async function(regenerate=false) {
            if (!this.name) {
                alert("Please select a statement set to load.");
                return;
            }
            const resp = await fetch(`${JSON_ADDR}${this.name}?regen=${regenerate}&grouped=false`, {method: 'GET'});
            console.log("getStmts response status: " + resp.status);
            const data = await resp.json();
            this.stmts = data.stmts;
            this.grouped = data.grouped;
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

