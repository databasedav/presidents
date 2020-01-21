module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  devServer: {
    proxy: {
      "/api/**": {
        target: "http://0.0.0.0:8001",
        pathRewrite: { '^/api': '' },
        changeOrigin: true
      },
      "/api/socket.io": {
        target: "http://0.0.0.0:8001",
        pathRewrite: { '^/api': '' },
        ws: true,
        changeOrigin: true
      }
    },
  },
  publicPath: 'src/front',
  outputDir: 'src/back/server/game_server/static',
  assetsDir: 'assets'
}