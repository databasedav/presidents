<template>
  <v-container>
    
    <v-layout column>
      <v-flex xs12>
        <OtherPlayerBox
          :namespace='this.namespace'
        >
        </OtherPlayerBox>
      </v-flex>
      
      <v-flex xs12>
        <AlertSnackbar
          :namespace='this.namespace'
        >
        </AlertSnackbar>
      </v-flex>
      
      <v-flex xs12>
        <InPlayBox
          :namespace='this.namespace'
        >
        </InPlayBox>
      </v-flex>
      
      <v-flex xs12>
        <MessageBox
          :namespace='this.namespace'
        >
        </MessageBox>
      </v-flex>

      <v-layout justify-center>
        <v-flex xs8>
          <PlayerStrip
            :namespace='this.namespace'
            :spot='this.spot'
          >
          </PlayerStrip>
        </v-flex>
      </v-layout>

      <CardBox
        :namespace='this.namespace'
        @card_click='this.card_click'
      >
      </CardBox>

      <v-flex xs12>
        <ButtonBox
          :namespace='this.namespace'
          @unlock='this.unlock'
          @lock='this.lock'
          @play='this.play'
          @unlock_pass='this.unlock_pass'
          @pass='this.pass'
          @ask='this.ask'
          @give='this.give'
          @asking_click='this.asking_click'
        >
        </ButtonBox>
      </v-flex>
    </v-layout>
    
  </v-container>
</template>

<script>
import CardBox from './CardBox.vue'
import ButtonBox from './ButtonBox.vue'
import InPlayBox from './InPlayBox.vue'
import AlertSnackbar from './AlertSnackbar.vue'
import MessageBox from './MessageBox.vue'
import PlayerStrip from './PlayerStrip.vue'
import OtherPlayerBox from './OtherPlayerBox.vue'

export default {
  name: 'Game',
  
  components: {
    CardBox,
    ButtonBox,
    InPlayBox,
    AlertSnackbar,
    MessageBox,
    PlayerStrip,
    OtherPlayerBox
  },

  props: {
    // server namespace
    server: String,
    // when true, plugs in testing socket and vuex module whose namespaces
    // are the id of the socket instead of the server namespace
    testing: {
      type: Boolean,
      default: false
    }
  },

  data () {
    return {
      socket: undefined
    }
  },

  created () {
    this.socket = this.$store.dispatch('plugin_server', {
      namespace: this.namespace,
      testing: this.testing
    })
  },

  methods: {
    card_click(card) {
      this.$store.dispatch(`${this.namespace}/emit_card_click`, {
        'card': card
      })
    },

    unlock () {
      this.$store.dispatch(`${this.namespace}/emit_unlock`)
    },

    lock () {
      this.$store.dispatch(`${this.namespace}/emit_lock`)
    },

    play () {
      this.$store.dispatch(`${this.namespace}/emit_play`)
    },

    unlock_pass () {
      this.$store.dispatch(`${this.namespace}/emit_unlock_pass`)
    },

    pass () {
      this.$store.dispatch(`${this.namespace}/emit_pass`)
    },

    ask () {
      this.$store.dispatch(`${this.namespace}/emit_ask`)
    },

    give () {
      this.$store.dispatch(`${this.namespace}/emit_give`)
    },

    asking_click (value) {
      this.$store.dispatch(`${this.namespace}/emit_asking_click`, {
        'value': value
      })
    }
  },

  computed: {
    namespace () {
      return this.socket ? this.socket.io.engine.id : null
    },

    on_turn () {
      return this.$store.state[this.namespace].on_turn
    },

    spot () {
      return this.$store.state[this.namespace].spot
    }
  },
}
</script>

<style>

</style>
