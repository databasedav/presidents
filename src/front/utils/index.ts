// import store from '../store/store'
import state from "../store/game_module/state";
import mutations from "../store/game_module/mutations";
import getters from "../store/game_module/getters";
import actions from "../store/game_module/actions";
import router from "../router";

// function namespaced_getter (namespace, getter) {
//     return store.getters[`${namespace}/${getter}`]
// }

function create_server_module() {
  return {
    strict: process.env.NODE_ENV !== "production",
    namespaced: true,
    state: state(),
    getters,
    mutations,
    actions
  };
}

function create_server_browser_module(rbnsp) {
  return {
    strict: process.env.NODE_ENV !== "production",

    namespaced: true,

    state: {
      rbnsp: rbnsp,
      // TODO: change to map once reactive
      servers: []
    },

    mutations: {
      SOCKET_refresh(state, payload) {
        state.servers = payload.servers;
      }
    },

    actions: {
      emit_refresh(context, payload) {
        this._vm.$socket[context.state.rbnsp].emit("refresh");
      },

      emit_add_server(context, payload) {
        this._vm.$socket[context.state.rbnsp].emit("add_server", payload);
      },

      emit_join_server(context, payload) {
        this._vm.$socket[context.state.rbnsp].emit("join_server", payload);
      },

      socket_send_to_server(context, payload) {
        router.push({
          name: "presidents",
          params: {
            rnsp: payload.rnsp
          }
        });
      }
    }
  };
}

const EVENTS = [
  "add_card",
  "alert",
  "clear_cards",
  "clear_hand_in_play",
  "deselect_card",
  "message",
  "remove_asking_option",
  "remove_card",
  "select_card",
  "set_asker",
  "set_asking_option",
  "set_cards_remaining",
  "set_dot_color",
  "set_giver",
  "set_gives",
  "set_giving_options",
  "set_hand_in_play",
  "set_names",
  "set_on_turn",
  "set_pass_unlocked",
  "set_spot",
  "set_takes",
  "set_time",
  "set_timer_state",
  "set_trading",
  "set_unlocked",
  "update_alert_str",
  "update_current_hand_str"
];

export { create_server_module, create_server_browser_module, EVENTS };
