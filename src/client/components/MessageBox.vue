<template>
  <v-textarea
    :id='this.id'
    :value='message'
    rows='10'
    no-resize
    readonly
    outline
  >
  </v-textarea>
</template>

<script>
import { mapState } from 'vuex'

export default {

  data () {
    return {
      text_area: HTMLElement
    }
  },

  props: {
    namespace: String
  },

  mounted () {
    this.text_area = document.getElementById(this.id)
    this.text_area.scrollTop = this.text_area.scrollHeight
  },

  watch: {
    text_area () {
      this.text_area.scrollTop = this.text_area.scrollHeight
    }
  },

  computed: {
    message () {
      this.text_area.scrollTop = this.text_area.scrollHeight
      return this.$store.state[this.namespace].message
    },

    id () {
      return 'message_box_' + this.namespace
    }
  },
}
</script>

<style>

</style>
