export default {
  emit_card_click (context, payload) {
    context.state.socket.emit('card_click', payload)
  },

  emit_unlock (context, payload) {
    context.state.socket.emit('unlock', payload)
  },

  emit_lock (context, payload) {
    context.state.socket.emit('lock', payload)
  },

  emit_play (context, payload) {
    context.state.socket.emit('play', payload)
  },

  emit_unlock_pass (context, payload) {
    context.state.socket.emit('unlock_pass', payload)
  },

  emit_pass (context, payload) {
    context.state.socket.emit('pass', payload)
  },

  emit_ask (context, payload) {
    context.state.socket.emit('ask', payload)
  },

  emit_give (context, payload) {
    context.state.socket.emit('give', payload)
  },

  emit_asking_click (context, payload) {
    context.state.socket.emit('asking_click', payload)
  }
}
