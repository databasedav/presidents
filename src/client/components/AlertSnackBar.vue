<template>
    <v-snackbar
      v-model='snackbar'
      :timeout='3000'
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
  name: 'AlertSnackBar',
  data () {  
    return {
      snackbar: false,
      alert: ''
    }
  },
  methods: {
    onClick_flush() {
      this.$snackbar.show(this.alert, {
        flushAll: true
      })
    }
  },
  computed: {
    // ...mapGetters(['alert', 'snackbar'])
  },
  // sockets: {
  //   alert (payload) {
  //     this.snackbar = true
  //     this.alert = payload.alert
  //   }
  // }
}


</script>
    