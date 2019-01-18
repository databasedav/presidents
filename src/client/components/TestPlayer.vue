<template>
  <v-container>
    <div v-if='on_turn' class='circle-green'>{{ spot }}</div>
    <div v-else class='circle-red'>{{ spot }}</div>

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
import io from 'socket.io-client'
import CardBox from './CardBox.vue'
import ButtonBox from './ButtonBox.vue'
import InPlayBox from './InPlayBox.vue'
import AlertSnackbar from './AlertSnackbar.vue'
import MessageBox from './MessageBox.vue'
import PlayerStrip from './PlayerStrip.vue'
import OtherPlayerBox from './OtherPlayerBox.vue'

import { create_namespaced_player_socket_plugin } from '../store/plugins'
import { createSinglePlayerStore, register_namespaced_module } from '../utils/utils'


export default {
  data () {
    return {
      socket: io.Socket
    }
  },

  props: {
    namespace: String
  },

  components: {
    CardBox,
    ButtonBox,
    InPlayBox,
    AlertSnackbar,
    MessageBox,
    PlayerStrip,
    OtherPlayerBox
  },

  created () {
    this.$store.registerModule(this.namespace, createSinglePlayerStore())
    this.socket = io(`//${window.location.host}`, { forceNew: true })
    this.socket.emit('join_room', {room: 'world', name: this.namespace})
    const plugin = create_namespaced_player_socket_plugin(this.socket, this.namespace)
    plugin(this.$store)
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
    on_turn () {
      return this.$store.state[this.namespace].on_turn
    },

    spot () {
      return this.$store.state[this.namespace].spot
    },

    time () {
      return this.$store.state[this.namespace].times[this.spot]
    }
  }
}
</script>

<style>
.circle-green {
  height: 50px;
  width: 50px;
  position: relative;
  left: 20px;
  top: 20px;
  background-color: rgb(54, 179, 16);
  border-radius: 50%;
}

.circle-red {
  height: 50px;
  width: 50px;
  position: relative;
  left: 20px;
  top: 20px;
  background-color: rgb(195, 15, 39);
  border-radius: 50%;
}
</style>
