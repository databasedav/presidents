// import io from 'socket.io-client'
// import { create_server_module, create_server_browser_module, EVENTS } from '../utils/utils'

// function server_browser_plugin (rbnsp) {
//   return store => {
//     store.registerModule(rbnsp, create_server_browser_module(rbnsp))
//     // TODO
//   }
// }

// function server_plugin ({ namespace, testing=false }) {
//   return store => {
//     // use actual server namespace to connect
//     // TODO: use single socket connection per browser
//     const socket = io(`http://127.0.0.1:5000${namespace}`, { forceNew: true })

//     socket.once('connect', function () {
//       // if testing (i.e. four player vue), use socket's id (client's sid) as namespace
//       // need to wait till socket connects to get its id (sid)
//       if (testing) namespace = socket.id
//       store.registerModule(namespace, create_server_module())
//       // register presidents event listeners
//       EVENTS.forEach(event => {
//         socket.on(event, payload => {
//           store.commit(`${namespace}/${event}`, payload)
//         })
//       })
//       // gives store access to namespaced socket
//       store.commit(`${namespace}/set_socket`, { 'socket': socket })
//     })
//   }
// }

// export { server_plugin, server_browser_plugin }
