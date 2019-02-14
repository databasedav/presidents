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

  name: 'Player',
  
  components: {
    CardBox,
    ButtonBox,
    InPlayBox,
    AlertSnackbar,
    MessageBox,
    PlayerStrip,
    OtherPlayerBox
  },

  methods: {
    restart () {
      this.socket.emit('restart')
    },

    card_click(card) {
      this.socket.emit('card_click', {'card': card})
    },

    unlock () {
      this.socket.emit('unlock')
    },

    lock () {
      this.socket.emit('lock')
    },

    play () {
      this.socket.emit('play')
    },

    unlock_pass () {
      this.socket.emit('unlock_pass')
    },

    pass () {
      this.socket.emit('pass')
    },

    ask () {
      this.socket.emit('ask')
    },

    give () {
      this.socket.emit('give')
    },

    asking_click (value) {
      this.socket.emit('asking_click', {'value': value})
    }
  },

  computed: {
    socket () {
      return this.$store.state.socket
    },

    namespace () {
      return this.$store.state.namespace
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
