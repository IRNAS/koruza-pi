#!/usr/bin/env python
import koruza
import time


class TestLatency(koruza.Application):
    application_id = 'test_latency'
    needs_remote = True

    last_sent_seqno = None
    last_rcvd_seqno = None
    last_publish = None

    def measure(self, remote_state, update_publish=True, increment=True):
        if update_publish:
            self.last_publish = time.time()
        if increment:
            self.last_sent_seqno += 1

        self.publish({
            'sent_seqno': self.last_sent_seqno,
            'sent_time': self.last_publish,
            'rcvd_seqno': self.last_rcvd_seqno,
            'rcvd_time': remote_state.get('app_status', {}).get('sent_time', None),
        })

        if update_publish or increment:
            print "Published:", self.last_sent_seqno, self.last_publish

    def on_idle(self, bus, state, remote_state):
        if remote_state.get('app_status', {}).get('sent_seqno', None) != self.last_rcvd_seqno:
            self.last_rcvd_seqno = remote_state['app_status']['sent_seqno']
            print "Got new measurement, republish", self.last_rcvd_seqno
            self.measure(remote_state, False, False)

        if self.last_sent_seqno is None:
            self.last_sent_seqno = 0
            self.measure(remote_state)
        elif remote_state.get('app_status', {}).get('rcvd_seqno', None) == self.last_sent_seqno:
            print "Seq:", self.last_sent_seqno, "RTT:", time.time() - remote_state['app_status']['rcvd_time']
            self.measure(remote_state)
        elif time.time() - self.last_publish > 10:
            print "Retry after 10 sec.", remote_state.get('app_status')
            self.measure(remote_state, increment=False)

TestLatency().start()
