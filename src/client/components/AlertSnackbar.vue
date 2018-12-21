<template>
    <v-snackbar
      v-model='snackbar'
      :timeout='1000'
      :top='true'
    >
      {{ alert }}
      <v-btn
        color="pink"
        flat
        @click="snackbar = false"
      >
        Close
      </v-btn>
    </v-snackbar>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'AlertSnackbar',
  // data () {  
  //   return {
  //     snackbar: false,
  //     alert: ''
  //   }
  // },

  props: {
    namespace: String
  },

  // methods: {
  //   onClick_flush() {
  //     this.$snackbar.show(this.alert, {
  //       flushAll: true
  //     })
  //   }
  // },
  
  computed: {
    snackbar () {
      return this.$store.getters[`${this.namespace}/snackbar`]
    },
    alert () {
      return this.$store.getters[`${this.namespace}/alert`]
    },
  },

  // watch: {
  //   alert () {
  //     this.$snackbar.show(this.alert, {
  //       flushAll: true
  //     })
  //   }
  // }
}


</script>
    