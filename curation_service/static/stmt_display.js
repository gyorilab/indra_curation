Vue.component('stmt-display', {
    template: `
        <div class='stmts'>
          <div class='header-row'>
            <h3 v-bind:title="metadata_display">Statements</h3>
            <button class="btn btn-primary" @click="loadAll">
              Load All
            </button>
            <div class="form-group ml-2 d-inline-flex">
              <input v-model='search'
                     id="filter-search"
                     placeholder="Search..."
                     class="form-control"/>
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
        }
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
        base_list: function () {
            // If we are searching, we need to filter the statements
            // based on the search string.
            if (!this.search) {
                return this.stmts;
            }
            let search = this.search.toLowerCase();
            return this.stmts.filter(stmt => {
                return stmt.english.toLowerCase().includes(search);
            });
        }
    },
    mixins: [pieceMealMixin]
})

