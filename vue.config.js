module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  devServer: {
    proxy: {
      ...['https://presidentsdotcom.azurewebsites.net/token', 'https://presidentsdotcom.azurewebsites.net/register', "https://presidentsdotcom.azurewebsites.net/create_game", "https://presidentsdotcom.azurewebsites.net/join_game", 'https://presidentsdotcom.azurewebsites.net/get_games'].reduce((acc, ctx) => ({...acc, [ctx]: {target: 'http://0.0.0.0:80', changeOrigin: true}}), {}),
      "/socket.io": {
        ws: true,
        target: "http://0.0.0.0:80",
        changeOrigin: true
      }
    },
  },
  outputDir: 'src/front/static'
}