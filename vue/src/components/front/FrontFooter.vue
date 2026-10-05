<template>
  <footer class="front-footer">
    <div class="front-shell front-footer__inner">
      <div class="front-footer__left">
        <div class="front-footer__brand">
          <img class="front-footer__logo" src="@/assets/logo.png" alt="" aria-hidden="true" />
          <span>{{ siteName }}</span>
        </div>
        <div class="front-footer__links">
          <a href="javascript:void(0)" @click.prevent>隐私政策</a>
          <a href="javascript:void(0)" @click.prevent>服务条款</a>
          <a href="javascript:void(0)" @click.prevent>帮助中心</a>
        </div>
        <p class="front-footer__copy">© {{ year }} {{ siteName }}. 保留所有权利.</p>
      </div>
      <div class="front-footer__hotline">
        <span class="front-footer__hotline-label">服务热线</span>
        <a class="front-footer__hotline-num" :href="`tel:${hotline}`">{{ hotline }}</a>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { SITE_NAME, SITE_COPYRIGHT_YEAR, SITE_HOTLINE } from '@/config/site'

const siteName = SITE_NAME
const year = SITE_COPYRIGHT_YEAR
const hotline = SITE_HOTLINE
</script>

<style scoped>
.front-footer {
  margin-top: auto;
  padding: 28px 0 32px;
  background: #1e2a24;
  color: rgba(255, 255, 255, 0.78);
}

.front-footer__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.front-footer__brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 12px;
}

.front-footer__logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  display: block;
  background: transparent;
}

.front-footer__links {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.front-footer__links a {
  color: rgba(255, 255, 255, 0.72);
  text-decoration: none;
  font-size: 13px;
}

.front-footer__links a:hover {
  color: #fff;
}

.front-footer__copy {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
}

.front-footer__hotline {
  text-align: right;
}

.front-footer__hotline-label {
  display: block;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 4px;
}

.front-footer__hotline-num {
  font-size: 26px;
  font-weight: 800;
  color: #7dd3a7;
  text-decoration: none;
  letter-spacing: 0.03em;
}

@media (max-width: 640px) {
  .front-footer__hotline {
    text-align: left;
    width: 100%;
  }
}
</style>
