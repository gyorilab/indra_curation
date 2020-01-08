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
                <div class='col-3 nvp clickable text-center'
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
              <ref-link v-if="'PMID' in text_refs" ref_name='pmid' :text_refs='text_refs'/>
              <ref-link v-else-if="'PMCID' in text_refs" ref_name='pmcid' :text_refs='text_refs'/>
              <ref-link v-else-if="'DOI' in text_refs" ref_name='doi' :text_refs='text_refs'/>
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

