module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  devServer: {
    proxy: {
      "/socket.io": {
        target: "http://0.0.0.0:8001",
        ws: true,
        changeOrigin: true
      }
    },
  },
}