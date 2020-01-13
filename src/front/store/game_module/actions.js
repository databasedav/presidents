export default {
  emit_game_action (context, payload) {
    context.state.socket.emit('game_action', payload)
  },

  disconnect_socket (context, payload) {
    context.state.socket.disconnect()
  }
};
