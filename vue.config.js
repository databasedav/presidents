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
  outputDir: process.env.NODE_ENV === 'production'
    ? './src/back/'
    : '.',
  assetsDir: process.env.NODE_ENV === 'production'
    ? 'static'
    : '.',
  indexPath: process.env.NODE_ENV === 'production'
    ? 'templates/index.html'
    : 'index.html',
  chainWebpack: config => {
    config
      .entry('app')
        .clear()
        .add('./src/front/main.js')
        .end()
  },
  configureWebpack: {
    devtool: 'source-map'
  }
};