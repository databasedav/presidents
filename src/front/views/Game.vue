<template>
  <v-container>
    <v-overlay
      :value="this.paused"
    >
      <v-row justify="center">
        <v-col cols="8">
          <v-alert :value="true" type="warning">
            the game has been paused since someone left; it will resume once their spot is filled (players: {{ num_players }}/4)
          </v-alert>
        </v-col>
      </v-row>
    </v-overlay>
    
    <v-row dense>
      <v-col cols="12">
        <AlertSnackbar 
          :namespace="this.namespace"
        ></AlertSnackbar>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <OtherPlayerBox
          :namespace="this.namespace"
        ></OtherPlayerBox>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <InPlayBox
          :namespace="this.namespace"
        ></InPlayBox>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <MessageBox
          :namespace="this.namespace"
        ></MessageBox>
      </v-col>
    </v-row>

    <v-row justify="center" dense>
      <v-col cols="9">
        <PlayerStrip
          :namespace="this.namespace"
          :spot="this.spot"
        ></PlayerStrip>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <CardBox
          :namespace="this.namespace"
          @card_click="this.card_click"
        ></CardBox>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <ButtonBox
          :namespace="this.namespace"
          @unlock="this.unlock"
          @lock="this.lock"
          @play="this.play"
          @unlock_pass="this.unlock_pass"
          @pass="this.pass"
          @ask="this.ask"
          @give="this.give"
          @asking_click="this.asking_click"
        ></ButtonBox>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import CardBox from "../components/CardBox.vue";
import ButtonBox from "../components/ButtonBox.vue";
import InPlayBox from "../components/InPlayBox.vue";
import AlertSnackbar from "../components/AlertSnackbar.vue";
import MessageBox from "../components/MessageBox.vue";
import PlayerStrip from "../components/PlayerStrip.vue";
import OtherPlayerBox from "../components/OtherPlayerBox.vue";

export default {
  name: "Game",

  components: {
    CardBox,
    ButtonBox,
    InPlayBox,
    AlertSnackbar,
    MessageBox,
    PlayerStrip,
    OtherPlayerBox
  },

  props: {
    game_id: null,
    // when true, plugs in testing socket and vuex module whose namespaces
    // are the id of the socket (sid) instead of the server namespace
    testing: {
      type: Boolean,
      default: false
    },
    testing_sid_index: Number
  },

  data () {
    return {
    };
  },

  watch: {
    game_id: {
      handler: function (game_id) {
        if (game_id) {
          this.$store.dispatch('join_game', {game_id: game_id, testing: this.testing, testing_username: 'abcd'[this.testing_sid_index-1]})
        }
      },
    }
  },

  methods: {
    card_click (card) {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'card_click',
        card: card
      })
    },

    unlock () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'unlock'
      });
    },

    lock () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'lock'
      });
    },

    play () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'play'
      });
    },

    unlock_pass () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'unlock_pass'
      });
    },

    pass () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'pass'
      });
    },

    ask () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'ask'
      });
    },

    give () {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'give'
      });
    },

    asking_click (rank) {
      this.$store.dispatch(`${this.namespace}/emit_game_action`, {
        action: 'asking_click',
        rank: rank
      });
    }
  },

  computed: {
    namespace () {
      return (this.testing && this.$store.state.testing_sids[this.testing_sid_index-1]) || this.game_id;
    },

    on_turn () {
      return this.$store.state[this.namespace].on_turn;
    },

    spot () {
      return this.$store.state[this.namespace].spot;
    },

    paused () {
      return this.$store.state[this.namespace].paused;
    },

    num_players () {
      return this.$store.state[this.namespace].names.filter(Boolean).length;
    }
  },

  beforeRouteLeave (to, from, next) {
    this.$store.dispatch(`${this.namespace}/disconnect_socket`)
    this.$store.unregisterModule(this.namespace)
    next()
  }
};
</script>