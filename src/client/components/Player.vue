<template>
  <div>
    <!-- <Listener
      :socket='this.socket'
      :namespace='this.namespace'
    ></Listener> -->
    <div v-if='this.on_turn' class='circle-green'>{{ this.spot }}</div>
    <div v-else class='circle-red'>{{ this.spot }}</div>
    <AlertSnackbar :namespace='this.namespace'></AlertSnackbar>
    <InPlayBox :namespace='this.namespace'></InPlayBox>
    <CardBox
      :namespace='this.namespace'
      @card_click='this.card_click'
    ></CardBox>
    <ButtonBox
      :namespace='this.namespace'
      @unlock='this.unlock'
      @lock='this.lock'
      @play='this.play'
      @pass='this.pass'
      @ask='this.ask'
      @give='this.give'
      @asking_click='this.asking_click'
    ></ButtonBox>
  </div>
</template>

<script>
import CardBox from './CardBox.vue'
import ButtonBox from './ButtonBox.vue'
import Listener from './Listener.vue'
import InPlayBox from './InPlayBox.vue'
import AlertSnackbar from './AlertSnackbar'


export default {

  name: 'Player',
  
  components: {
    CardBox,
    Listener,
    ButtonBox,
    InPlayBox,
    AlertSnackbar
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