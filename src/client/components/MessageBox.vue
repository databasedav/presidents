<template>
  <v-textarea
    :value='message'
    rows='2'
    disabled
    no-resize
    readonly
    outline
    autofocus
  >
  </v-textarea>
</template>

<script>
import { mapState } from 'vuex'

export default {

  props: {
    namespace: String
  },

  computed: {
    message () {
      return this.$store.state[this.namespace].message
    }
  },
}
</script>

<style>

</style>
