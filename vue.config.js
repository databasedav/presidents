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

  // document why I am doing everything below
  outputDir: process.env.NODE_ENV === 'production'
    ? './src/back/app'
    : './public',  // don't understand why this makes it work; results in "don't set output directory to project root" error when just '.'
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