Vue.component('stmt-display', {
    template: `
        <div class='stmts'>
          <div class='header-row'>
            <button class="btn btn-primary" @click="loadAll">
              Load All
            </button>
            <div class="form-group ml-2 d-inline-flex">
              <input v-model='search'
                     id="filter-search"
                     placeholder="Search..."
                     class="form-control"/>
            </div>
            <div class="custom-control custom-switch">
              <input type="checkbox"
                     class="custom-control-input"
                     v-model="filter_curations"
                     id="filter-curations">
              <label class="custom-control-label" for="filter-curations">Filter curations</label>
            </div>
          </div>
          <div v-if='grouped'>
            <top-group v-for='top_group in list_shown'
                       :key='top_group.html_key'
                       v-bind='top_group'/>
          </div>
          <div v-else>
            <statement v-for='stmt in list_shown'
                       :key='stmt.hash'
                       v-bind='stmt'/>
          </div>
          <div v-if='!autoload'
               class='text-center clickable'
               v-show='show_buttons'
               v-on:click='loadMore'>
            Load {{ next_batch }} more...
          </div>
          <div v-if='!autoload'
               class='text-center clickable'
               v-show='show_buttons'
               v-on:click='loadAll'>
            Load all {{ stmts.length - end_n }} remaining...
          </div>
        </div>
      </div>
      `,
    props: {
        stmts: Array,
        metadata: Object,
        source_key_dict: Object,
        grouped: Boolean
    },
    data: function () {
        return {
            search: '',
            filter_curations: false,
            curation_hashes: new Set() // Set of hashes for curated statements
        }
    },
    methods: {
        getCurations: function () {
            fetch(CURATION_LIST_ADDR, {method: 'GET'})
                .then(response => response.json())
                .then(data => {
                    // Fill with hashes for each curation
                    // Each curation in the data is a list of curation entries
                    // {[stmt_hash, source_hash]: [{curation_entry1}, {curation_entry2}, ...]}
                    // We want to get a list of unique statement hashes.
                    this.curation_hashes = new Set(data.map(({ key }) => key[0]));
                });
        },
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
        extended_stmts: function () {
            // Add untagged_english to each statement
            return this.stmts.map(stmt => {
                let tag = document.createElement('div');
                tag.innerHTML = stmt.english;
                // Get inner text
                let untagged_english = tag.innerText;
                // Set the untagged_english property
                stmt = {...stmt, untagged_english: untagged_english};
                return stmt;
            });
        },
        base_list: function () {
            console.log(`Filter curations is now ${this.filter_curations}`);
            // If there are no curations, get them.
            if (this.curation_hashes.size === 0) {
                this.getCurations();
            }
            let search = this.search.toLowerCase();
            return this.extended_stmts.filter(stmt => {
                // Filter out curated statements if the switch is on and filter on search
                // term unless the search term is empty.
                if (this.filter_curations & this.curation_hashes.has(stmt.hash)) {
                    return false;
                }
                return stmt.untagged_english.toLowerCase().includes(search);
            });
        }
    },
    mixins: [pieceMealMixin]
})

