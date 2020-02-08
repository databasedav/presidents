module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  devServer: {
    proxy: {
      ...['/token', '/register', "/create_game", "/join_game", '/get_games'].reduce((acc, ctx) => ({...acc, [ctx]: {target: 'http://0.0.0.0:8000', changeOrigin: true}}), {}),
      "/socket.io": {
        ws: true,
        target: "http://0.0.0.0:8000",
        changeOrigin: true
      }
    },
  },
  outputDir: 'src/back/services/game_server/static',
  assetsDir: 'assets'
}