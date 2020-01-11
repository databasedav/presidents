module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  devServer: {
    proxy: {
      "/game_server": {
        target: "http://0.0.0.0:8001",
        pathRewrite: {"^/game_server" : ""},
        changeOrigin: true
      },
      "/socket.io": {
        target: "http://0.0.0.0:8001",
        ws: true,
        changeOrigin: true
      }
    },
  },
}