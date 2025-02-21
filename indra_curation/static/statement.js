Vue.component('statement', {
    template: `
        <div class='statement'>
          <h4 v-on:click='toggleList' class='clickable'>
            <span v-html='english'></span>
            <small class='badge badge-secondary badge-pill'>
              {{ evidence.length }}
            </small>
            <small v-if='total_curations'
                   class='badge badge-success badge-pill'>
               &#9998; {{ total_curations }}
            </small>
          </h4>
          <div class='ev-list' v-show='show_list'>
            <evidence v-for='ev in list_shown'
                      :key='ev.html_key'
                      v-bind='ev'
                      :stmt_hash='hash'/>
            <div class='text-center clickable'
                 v-show='show_buttons'
                 v-on:click='loadMore'>
              Load {{ next_batch }} more...
            </div>
            <div class='text-center clickable'
                 v-show='show_buttons'
                 v-on:click='loadAll'>
              Load all {{ evidence.length - end_n }} remaining...
            </div>
          </div>
        </div>
        `,
    props: {
        evidence: Array,
        english: String,
        hash: String
    },
    data: function () {
        return {
            html_key_set: new Set(),
        }
    },
    computed: {
        base_list: function() {
            // Return the evidence list, extend each evidence with a key
            return this.evidence.map(ev => {
                let html_key = "";
                if (!this.html_key_set.has(ev.source_hash)) {
                    html_key = ev.source_hash;
                } else {
                    html_key = ev.source_hash + '_' + this.html_key_set.size;
                }
                this.html_key_set.add(html_key);
                ev.html_key = html_key;
                return ev;
            });
        },

        total_curations: function() {
            var total_curations = 0;
            for (var ev in this.evidence.slice(0, this.end_n)) {
                total_curations += this.evidence[ev].num_curations > 0;
            }
            return total_curations;
        }
    },
    mixins: [expanderMixin, pieceMealMixin]
})

