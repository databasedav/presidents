<template>
  <div>
    <Listener
      :socket='socket'
      :namespace='namespace'
    ></Listener>
    <div v-if='on_turn' class='circle-green'>{{ spot }}</div>
    <div v-else class='circle-red'>{{ spot }}</div>
    <AlertSnackbar :namespace='namespace'></AlertSnackbar>
    <InPlayBox :namespace='namespace'></InPlayBox>
    <CardBox
      :namespace='namespace'
      @card_click='card_click'
    ></CardBox>
    <ButtonBox
      :namespace='namespace'
      @restart='restart'
      @unlock='unlock'
      @lock='lock'
      @play='play'
      @pass='pass'
    ></ButtonBox>
  </div>
</template>

<script>
import io from 'socket.io-client'
import CardBox from './CardBox.vue'
import ButtonBox from './ButtonBox.vue'
import Listener from './Listener.vue'
import InPlayBox from './InPlayBox.vue'
import AlertSnackbar from './AlertSnackbar'

import { namespaced_getter } from '../utils/utils'


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
    Listener,
    ButtonBox,
    InPlayBox,
    AlertSnackbar
  },

  created () {
    this.socket = io(`//${window.location.host}`, { forceNew: true })
  },

  methods: {
    restart () {
      this.socket.emit('restart')
    },

    card_click(card) {
      this.socket.emit('card_click', {'card': card})
    },

    restart () {
      this.socket.emit('restart')
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

    pass () {
      this.socket.emit('pass')
    }
  },

  computed: {
    on_turn () {
      return namespaced_getter(this.namespace, 'on_turn')
    },

    spot () {
      return namespaced_getter(this.namespace, 'spot')
    }
  },
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