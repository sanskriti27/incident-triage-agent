package com.example.controller;

import com.example.model.Order;
import com.example.payment.PaymentService;
import com.example.repository.OrderRepository;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@RestController
@RequestMapping("/orders")
public class OrderController {

    private static final Logger log = LoggerFactory.getLogger(OrderController.class);

    @Autowired
    private PaymentService paymentService;

    @Autowired
    private OrderRepository orderRepository;

    @GetMapping("/{orderId}")
    public ResponseEntity<?> getOrder(@PathVariable String orderId) {
        return ResponseEntity.ok(orderRepository.findById(orderId));
    }

    @DeleteMapping("/{orderId}")
    public ResponseEntity<?> cancelOrder(@PathVariable String orderId) {
        Order order = orderRepository.findById(orderId);
        order.cancel();
        return ResponseEntity.ok().build();
    }

    @PutMapping("/{orderId}")
    public ResponseEntity<?> updateOrder(@PathVariable String orderId, @RequestBody Order updates) {
        Order order = orderRepository.findById(orderId);
        order.merge(updates);
        orderRepository.save(order);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/checkout")
    public ResponseEntity<?> checkout(@RequestBody Order order) {
        log.info("Checkout request for userId={}", order.getUserId());
        String userId = order.getUserId();
        double amount = order.getAmount();
        log.info("Delegating to PaymentService userId={} amount={}", userId, amount);
        paymentService.processPayment(userId, amount);
        return ResponseEntity.ok().build();
    }
}
