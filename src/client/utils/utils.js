import store from '../store/store'

function namespaced_getter (namespace, getter) {
    return store.getters[`${namespace}/${getter}`]
}

export { namespaced_getter }