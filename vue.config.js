module.exports = {
  devServer: {
    proxy: {
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  outputDir: './src/server/',
  assetsDir: 'static',
  indexPath: 'templates/index.html',
  chainWebpack: config => {
    config
      .entry('app')
        .clear()
        .add('./src/client/main.js')
        .end()
  }
};