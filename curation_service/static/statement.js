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
                      :key='ev.source_hash'
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
    computed: {
        base_list: function() {
            return this.evidence;
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

