<script setup>
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
</script>

<template>
  <el-container style="height: 100vh">
    <el-header style="padding: 0; height: 56px">
      <AppHeader />
    </el-header>
    <el-container>
      <el-aside width="220px" style="background: #001529">
        <AppSidebar />
      </el-aside>
      <el-main style="background: #f0f2f5; padding: 20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
