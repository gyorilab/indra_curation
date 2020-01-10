var expanderMixin = {
    data: function () {
        return {
            show_list: false,
        }
    },
    methods: {
        toggleList: function() {
            this.show_list = !this.show_list;
        },
    }
}

var pieceMealMixin = {
    data: function() {
        return {
            end_n: 10,
            dn: 10,
            bottom: false
        }
    },
    created: function() {
        window.addEventListener('scroll', () => {
            this.bottom = this.bottomVisible()
        })
    },
    computed: {
        list_shown: function() {
            if (!this.base_list)
                return;
            return this.base_list.slice(0, this.end_n);
        },
        next_batch: function() {
            return Math.min(this.base_list.length - this.end_n, this.dn);
        },
        show_buttons: function() {
            return this.next_batch > 0;
        }
    },
    methods: {
        loadMore: function() {
            this.end_n += this.dn;
        },

        loadAll: function() {
            this.end_n = this.base_list.length;
        },

        bottomVisible: function() {
            const scrollY = window.scrollY;
            const visible = document.documentElement.clientHeight;
            const pageHeight = document.documentElement.scrollHeight;
            const bottomOfPage = visible + scrollY >= pageHeight;
            return bottomOfPage || pageHeight < visible;
        }
    },
    watch: {
        bottom: function(bottom) {
            if (bottom) {
                this.loadMore()
            }
        }
    }
}

