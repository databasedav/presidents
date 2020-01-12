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
      "/game_server/socket.io": {
        target: "http://0.0.0.0:8001",
        pathRewrite: {"^/game_server" : ""},
        ws: true,
        changeOrigin: true
      }
    },
  },
}