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
    ? './src/server/'
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
        .add('./src/client/main.js')
        .end()
  }
};