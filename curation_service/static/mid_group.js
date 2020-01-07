Vue.component('mid-group', {
    template: `
        <div class='mid-group' >
          <h4 v-if='stmt_info_list.length > 1'
              :class='{faded: show_list}'
              class='clickable'
              v-on:click='toggleList'>
            <span v-html='short_name'></span>
            <small class='badge badge-secondary badge-pill'>
              +
            </small>
          </h4>
          <div class='mid-list'
               :class='{ indented: stmt_info_list.length > 1 }'
               v-show='stmt_info_list.length <= 1 || show_list'>
            <statement v-for='stmt in list_shown'
                      :key='stmt.hash'
                      v-bind='stmt'/>
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
        stmt_info_list: Array,
        short_name: String,
        short_name_key: String,
    },
    computed: {
        base_list: function () {
            return this.stmt_info_list;
        }
    },
    mixins: [expanderMixin, pieceMealMixin]
})

