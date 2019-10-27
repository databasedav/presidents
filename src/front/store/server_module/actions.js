export default {
  emit_card_click (context, payload) {
    context.state.socket.emit('card_click', payload)
  },

  emit_unlock (context) {
    context.state.socket.emit('unlock')
  },

  emit_lock (context) {
    context.state.socket.emit('lock')
  },

  emit_play (context) {
    context.state.socket.emit('play')
  },

  emit_unlock_pass (context) {
    context.state.socket.emit('unlock_pass_turn')
  },

  emit_pass (context) {
    context.state.socket.emit('pass_turn')
  },

  emit_ask (context) {
    context.state.socket.emit('ask')
  },

  emit_give (context) {
    context.state.socket.emit('give')
  },

  emit_asking_click (context, payload) {
    context.state.socket.emit('asking_click', payload)
  }
}
