import state from "../store/game_module/state";
import mutations from "../store/game_module/mutations";
import getters from "../store/game_module/getters";
import actions from "../store/game_module/actions";


function create_game_module() {
  return {
    strict: process.env.NODE_ENV !== "production",
    namespaced: true,
    state: state(),
    getters,
    mutations,
    actions
  };
}

const EVENTS = [
  "add_card",
  "alert",
  "clear_cards",
  "clear_hand_in_play",
  "deselect_card",
  "increment_hand_just_played_count",
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
  "set_hand_just_played_count",
  "set_names",
  "set_on_turn",
  "set_pass_unlocked",
  "set_paused",
  "set_spot",
  "set_takes",
  "set_time",
  "set_timer_state",
  "set_trading",
  "set_unlocked",
  "update_alert_str",
  "update_current_hand_str",
];

export { create_game_module, EVENTS };
