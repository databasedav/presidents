<template>
  <div>
    <Receiver
      :socket='this.socket'
      :namespace='this.namespace'
    ></Receiver>
    <div v-if='on_turn' class='circle-green'></div>
    <div v-else class='circle-red'></div>
    <AlertSnackbar :namespace='this.namespace'></AlertSnackbar>
    <!-- <InPlayBox/> -->
    <CardBox
      :socket='this.socket'
      :namespace='this.namespace'
    ></CardBox>
    <ButtonBox :socket='this.socket' :namespace='this.namespace'></ButtonBox>
  </div>
</template>

<script>
import io from 'socket.io-client'
import CardBox from './CardBox.vue'
import ButtonBox from './ButtonBox.vue'
import Receiver from './Receiver.vue'
import InPlayBox from './InPlayBox.vue'
import AlertSnackbar from './AlertSnackbar'



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
    Receiver,
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
    }
  },

  computed: {
    on_turn () {
      return this.$store.getters[`${this.namespace}/on_turn`]
    }
  },

  




}
</script>

<style>
.circle-green {
  height: 20px;
  width: 20px;
  position: relative;
  left: 20px;
  top: 20px;
  background-color: rgb(54, 179, 16);
  border-radius: 50%;
}

.circle-red {
  height: 20px;
  width: 20px;
  position: relative;
  left: 20px;
  top: 20px;
  background-color: rgb(195, 15, 39);
  border-radius: 50%;
}
</style>