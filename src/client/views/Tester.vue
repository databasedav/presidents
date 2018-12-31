<template>
    <div>
        <Player :namespace='"a"'></Player>
        <Player :namespace='"b"'></Player>
        <Player :namespace='"c"'></Player>
        <Player :namespace='"d"'></Player>
    </div>
</template>

<script>
import Player from '../components/Player.vue'

export default {
    name: 'Tester',
    components: {
        Player
    }
}
</script>

<style>

</style>
