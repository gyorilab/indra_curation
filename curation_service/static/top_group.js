Vue.component('top-group', {
    template: `
        <div class='top-group'>
          <h4 v-if='stmts_formatted.length > 1'
              :class='{faded: show_list}'
              class='clickable'
              v-on:click='toggleList'>
            <span v-html='label'></span>
            <small class='badge badge-secondary badge-pill'>
              ++
            </small>
          </h4>
          <div class='top-list'
               :class='{ indented: stmts_formatted.length > 1 }'
               v-show='stmts_formatted.length <= 1 || show_list'>
            <mid-group v-for='mid_group in list_shown'
                       :key='mid_group.short_name_key'
                       v-bind='mid_group'/>
            <div class='text-center clickable'
                 v-show='show_buttons'
                 v-on:click='loadMore'>
              Load {{ next_batch }} more...
            </div>
            <div class='text-center clickable'
                 v-show='show_buttons'
                 v-on:click='loadAll'>
              Load all...
            </div>
          </div>
        </div>
        `,
    props: {
        stmts_formatted: Array,
        label: String,
    },
    computed: {
        base_list: function () {
            return this.stmts_formatted;
        },
    },
    mixins: [expanderMixin, pieceMealMixin]
})

